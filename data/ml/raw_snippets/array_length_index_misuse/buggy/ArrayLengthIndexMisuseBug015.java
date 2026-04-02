public class ArrayIndexBug015 {
    public void swapEnds(int[] arr) {
        int temp = arr[0];
        arr[0] = arr[arr.length];
        arr[arr.length] = temp;
    }
}