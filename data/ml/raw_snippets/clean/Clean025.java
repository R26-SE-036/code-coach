public class Clean025 {
    public int sumRange(int[] arr, int start, int end) {
        int sum = 0;
        for (int i = start; i <= end && i < arr.length; i++) {
            sum += arr[i];
        }
        return sum;
    }
}
