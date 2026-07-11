public class GenOffByOneFix162 {
    static int countAbove(int[] weights, int threshold) {
        int hits = 0;
        for (int i = 0; i < weights.length; i++) {
            if (weights[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static int sum1(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
