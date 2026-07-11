public class GenMissingBreakFix064 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
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

    static String describe4(int limit) {
        if (limit < 100) {
            return "low";
        } else if (limit > 500) {
            return "high";
        }
        return "medium";
    }

    static String describeItem(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "new";
                break;
            case 3:
                label = "closed";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
