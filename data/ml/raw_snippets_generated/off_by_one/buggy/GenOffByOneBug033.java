public class GenOffByOneBug033 {
    static int countAbove(int[] marks, int threshold) {
        int hits = 0;
        for (int i = 0; i <= marks.length; i++) {
            if (marks[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
