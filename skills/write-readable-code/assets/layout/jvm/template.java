package com.example.component;

import java.util.List;

public final class PublicType {
    public static final int PUBLIC_CONSTANT = 1;
    static final int PACKAGE_CONSTANT = 2;
    private static final int PRIVATE_CONSTANT = 3;

    public PublicType() {}

    public void publicMethod() {}

    void packageMethod() {}

    protected void protectedMethod() {}

    private void privateMethod() {}

    private static final class PrivateNestedType {}
}

// Prefer one top-level public type per file.
// Package-private top-level helpers may follow when justified.
final class PackagePrivateHelper {}
