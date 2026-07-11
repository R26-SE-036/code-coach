public class GenMissingBreakBug081 {
    static int sum1(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "shipped";
            case 2:
                label = "draft";
                break;
            case 3:
                label = "new";
                break;
            case 4:
                label = "queued";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int largest3(int[] ratings) {
        int best = ratings[0];
        for (int i = 1; i < ratings.length; i++) {
            if (ratings[i] > best) {
                best = ratings[i];
            }
        }
        return best;
    }
}
