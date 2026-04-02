public class OffByOneFix012 {
    public void checkBounds(int[] right) {
        int left = 0;
        while(left < right.length) {
            left++;
        }
    }
}