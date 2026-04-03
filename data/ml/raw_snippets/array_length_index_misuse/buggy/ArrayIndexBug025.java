public class ArrayIndexBug025 {
    public void replaceLast(boolean[] flags) {
        flags[flags.length] = false;
    }
}