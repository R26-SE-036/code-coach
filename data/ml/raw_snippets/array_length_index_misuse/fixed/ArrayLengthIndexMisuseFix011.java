public class ArrayIndexFix011 {
    public int getCombinedEnd(int[] arr1, int[] arr2) {
        int[] combined = new int[arr1.length + arr2.length];
        return combined[combined.length - 1];
    }
}