#### cpy_recur.bat
**Usage:**
<pre>
cpy_recur.bat C:\folder1 C:\folder2
</pre>

**Flag explanation:**
/e Copies directories and subdirectories, including empty ones.
/k Copies attributes. Normal Xcopy will reset read-only attributes.
/h Copies hidden and system files also.
/i If destination does not exist and copying more than one file, assume destination is a directory.
