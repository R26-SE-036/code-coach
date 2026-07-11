public class GenOffByOneBug151 {
    static int largest1(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "final";
        }
        return label;
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
}
