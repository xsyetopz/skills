package com.example.component

const val PUBLIC_CONSTANT = 1
internal const val MODULE_CONSTANT = 2
private const val PRIVATE_CONSTANT = 3

open class PublicType {
    fun publicMethod(): Int = privateMethod() + MODULE_CONSTANT

    internal fun moduleMethod(): Int = PUBLIC_CONSTANT

    protected open fun protectedMethod(): Int = PRIVATE_CONSTANT

    private fun privateMethod(): Int = protectedMethod()
}

internal class InternalType {
    fun run(): Int = PublicType().publicMethod()
}

private class FilePrivateType
