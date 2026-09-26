package constructs

// Read from Representation.kt so the access crosses a file (class) boundary.
val PLAIN_BUFFER_SIZE = 8_192

const val CONST_BUFFER_SIZE = 8_192

class Point(x: Int, y: Int) {
    val x: Int = x

    @JvmField
    val y: Int = y

    companion object {
        fun origin(): Int = 0

        @JvmStatic
        fun originStatic(): Int = 0
    }
}
