# require() halts evaluation when the executable is missing.

tool := require("definitely-not-installed-tool")

use-tool:
    @echo "{{ tool }}"
