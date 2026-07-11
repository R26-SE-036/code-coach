public class GenMissingBreakBug153 {
    static void printAll1(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void printAll3(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static String describe4(int limit) {
        if (limit < 100) {
            return "low";
        } else if (limit > 500) {
            return "high";
        }
        return "medium";
    }

    static String describe5(int total) {
        if (total < 10) {
            return "low";
        } else if (total > 50) {
            return "high";
        }
        return "medium";
    }

    static int largest6(int[] sizes) {
        int best = sizes[0];
        for (int i = 1; i < sizes.length; i++) {
            if (sizes[i] > best) {
                best = sizes[i];
            }
        }
        return best;
    }

    static int largest7(int[] prices) {
        int best = prices[0];
        for (int i = 1; i < prices.length; i++) {
            if (prices[i] > best) {
                best = prices[i];
            }
        }
        return best;
    }

    static String describeItem(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "closed";
            case 3:
                label = "new";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static boolean isEven8(int count) {
        return count % 2 == 0;
    }
}
