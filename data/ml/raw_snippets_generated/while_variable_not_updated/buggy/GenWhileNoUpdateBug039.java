public class GenWhileNoUpdateBug039 {
    static String describe1(int quota) {
        if (quota < 5) {
            return "low";
        } else if (quota > 20) {
            return "high";
        }
        return "medium";
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static int largest3(int[] values) {
        int best = values[0];
        for (int i = 1; i < values.length; i++) {
            if (values[i] > best) {
                best = values[i];
            }
        }
        return best;
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void pump(boolean running, int limit) {
        while (!running) {
            System.out.println(limit);
            limit++;
        }
    }
}
