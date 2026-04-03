public class ArrayIndexFix029 {
    public int fallbackTail(int[] arr) {
        return arr.length > 0 ? arr[arr.length - 1] : 0;
    }
}