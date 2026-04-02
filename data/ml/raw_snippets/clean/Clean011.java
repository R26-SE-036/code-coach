public class Clean011 {
    public void loopFromOne(int[] arr) {
        for(int i = 1; i < arr.length; i++) {
            arr[i] = arr[i - 1] + 1;
        }
    }
}