<h3>1. cpy_recur.bat</h3>

1. **Usage:**

<pre>
cpy_recur.bat C:\folder1 C:\folder2
</pre>

1. **Flag Explanation:**
1. /e Copies directories and subdirectories, including empty ones.
1. /k Copies attributes. Normal Xcopy will reset read-only attributes.
1. /h Copies hidden and system files also.
1. /i If destination does not exist and copying more than one file, assume destination is a directory.
