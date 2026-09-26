using System.Security.Cryptography;
using System.Text;

// Derives a deterministic key for the given passphrase: dotnet run -- <passphrase>
string passphrase = args.Length > 0 ? args[0] : "correct horse battery staple";
byte[] salt = Encoding.UTF8.GetBytes("keytool-salt-v1");
using var kdf = new Rfc2898DeriveBytes(passphrase, salt, 100_000, HashAlgorithmName.SHA256);
Console.WriteLine(Convert.ToHexString(kdf.GetBytes(32)));
