public class GenOffByOneBug116 {
    static int countAbove(int[] marks, int threshold) {
        int hits = 0;
        for (int i = 0; i <= marks.length; i++) {
            if (marks[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }
}
