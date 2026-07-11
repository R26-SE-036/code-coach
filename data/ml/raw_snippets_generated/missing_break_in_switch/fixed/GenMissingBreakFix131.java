public class GenMissingBreakFix131 {
    static int largest1(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }

    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "shipped";
                break;
            case 4:
                label = "queued";
                break;
            case 5:
                label = "paid";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static int sum2(int[] weights) {
        int total = 0;
        for (int i = 0; i < weights.length; i++) {
            total += weights[i];
        }
        return total;
    }
}
