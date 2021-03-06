<h3>1. cpy_recur.bat</h3>

1. **Usage:**

<pre>
cpy_recur.bat C:\folder1 C:\folder2
</pre>

2. **Flag Explanation:**
a. /e Copies directories and subdirectories, including empty ones.
b. /k Copies attributes. Normal Xcopy will reset read-only attributes.
c. /h Copies hidden and system files also.
d. /i If destination does not exist and copying more than one file, assume destination is a directory.
