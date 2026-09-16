using System;
using System.Buffers;

public static class OwnershipTests
{
    public static int AllocateChecksum(ReadOnlySpan<byte> input)
    {
        byte[] buffer = input.ToArray();
        int sum = 0;
        foreach (byte value in buffer)
            sum = checked(sum + value);
        return sum;
    }

    public static int PooledChecksum(ReadOnlySpan<byte> input) =>
        PoolChecksum(input, ArrayPool<byte>.Shared);
    // Correctness example, not a claim that pooling this tiny operation is faster.
    private static int PoolChecksum(
        ReadOnlySpan<byte> input,
        ArrayPool<byte> pool,
        bool injectFailure = false
    )
    {
        byte[] buffer = pool.Rent(input.Length);
        try
        {
            input.CopyTo(buffer.AsSpan(0, input.Length));
            if (injectFailure)
                throw new InvalidOperationException("injected failure");
            int sum = 0;
            foreach (byte value in buffer.AsSpan(0, input.Length))
                sum = checked(sum + value);
            return sum;
        }
        finally
        {
            // Clear explicitly if wiping is required even when the pool discards the array.
            buffer.AsSpan(0, input.Length).Clear();
            pool.Return(buffer, clearArray: true);
        }
    }

    private sealed class DirtyOversizedPool : ArrayPool<byte>
    {
        public int Returns { get; private set; }
        private byte[]? rented;
        private int logicalLength;

        public override byte[] Rent(int minimumLength)
        {
            if (rented is not null)
                throw new InvalidOperationException("already rented");
            logicalLength = minimumLength;
            rented = new byte[checked(minimumLength + 17)];
            Array.Fill(rented, (byte)255);
            return rented;
        }

        public override void Return(byte[] array, bool clearArray = false)
        {
            if (!ReferenceEquals(array, rented))
                throw new InvalidOperationException("wrong pool/double return");
            if (!clearArray)
                throw new InvalidOperationException("clear requested by contract");
            for (int i = 0; i < logicalLength; i++)
                if (array[i] != 0)
                    throw new InvalidOperationException("logical data not cleared before return");
            // Model a pool that discards the buffer without clearing it itself.
            rented = null;
            Returns++;
        }
    }

    [Flags]
    private enum Bits
    {
        None = 0,
        Read = 1,
        Write = 2,
    }

    public static void Verify()
    {
        var pool = new DirtyOversizedPool();
        if (PoolChecksum(new byte[] { 1, 2, 3 }, pool) != 6 || pool.Returns != 1)
            throw new InvalidOperationException("pool initialized-length contract");
        if (PoolChecksum(Array.Empty<byte>(), pool) != 0 || pool.Returns != 2)
            throw new InvalidOperationException("empty pooled input");

        bool observedFailure = false;
        try
        {
            PoolChecksum(new byte[] { 1, 2, 3 }, pool, injectFailure: true);
        }
        catch (InvalidOperationException error) when (error.Message == "injected failure")
        {
            observedFailure = true;
        }
        if (!observedFailure || pool.Returns != 3)
            throw new InvalidOperationException(
                "exception path must return the buffer exactly once"
            );

        Bits value = Bits.Read,
            composite = Bits.Read | Bits.Write;
        if (!value.HasFlag(Bits.None) || value.HasFlag(composite))
            throw new InvalidOperationException("HasFlag expected result");
        if ((value & composite) == 0)
            throw new InvalidOperationException("any-bit differs from all-bit test");

        byte[] input = { 0, 1, 2, byte.MaxValue };
        if (AllocateChecksum(input) != PooledChecksum(input))
            throw new InvalidOperationException("allocation/pool checksum");
    }
}
