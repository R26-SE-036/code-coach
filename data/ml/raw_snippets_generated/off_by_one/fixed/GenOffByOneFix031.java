public class GenOffByOneFix031 {
    static int countAbove(int[] marks, int threshold) {
        int hits = 0;
        for (int i = 0; i < marks.length; i++) {
            if (marks[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
