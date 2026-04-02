public class OffByOneBug011 {
    public void reverseProcess(int[] arr) {
        for (int i = arr.length; i > 0; i--) {
            System.out.println(arr[i]);
        }
    }
}