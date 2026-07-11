public class GenOffByOneBug161 {
    static int countAbove(int[] ages, int threshold) {
        int hits = 0;
        for (int i = 0; i <= ages.length; i++) {
            if (ages[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
