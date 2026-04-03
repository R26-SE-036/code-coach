public class Clean027 {
    public int countMatches(int[] arr, int value) {
        int count = 0;
        for (int elem : arr) {
            if (elem == value) {
                count++;
            }
        }
        return count;
    }
}
