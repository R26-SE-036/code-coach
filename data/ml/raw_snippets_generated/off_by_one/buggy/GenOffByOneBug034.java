public class GenOffByOneBug034 {
    static int largest1(int[] sizes) {
        int best = sizes[0];
        for (int i = 1; i < sizes.length; i++) {
            if (sizes[i] > best) {
                best = sizes[i];
            }
        }
        return best;
    }

    static boolean isEven2(int stock) {
        return stock % 2 == 0;
    }

    static int countAbove(int[] ratings, int threshold) {
        int hits = 0;
        for (int i = 0; i <= ratings.length; i++) {
            if (ratings[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static int sum3(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }
}
