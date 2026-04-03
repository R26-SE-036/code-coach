public class Clean028 {
    public void shiftLeft(int[] arr) {
        if (arr.length == 0) {
            return;
        }
        int first = arr[0];
        for (int i = 0; i < arr.length - 1; i++) {
            arr[i] = arr[i + 1];
        }
        arr[arr.length - 1] = first;
    }
}
