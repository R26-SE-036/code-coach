public class ArrayIndexBug016 {
    public int readLastCopyValue(int[] source) {
        int[] copy = new int[source.length];
        return copy[copy.length];
    }
}