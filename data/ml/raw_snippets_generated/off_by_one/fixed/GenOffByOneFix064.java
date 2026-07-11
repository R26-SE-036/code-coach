public class GenOffByOneFix064 {
    static int countAbove(int[] ratings, int threshold) {
        int hits = 0;
        for (int i = 0; i < ratings.length; i++) {
            if (ratings[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static int largest2(int[] marks) {
        int best = marks[0];
        for (int i = 1; i < marks.length; i++) {
            if (marks[i] > best) {
                best = marks[i];
            }
        }
        return best;
    }
}
