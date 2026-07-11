public class GenWhileNoUpdateFix114 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static boolean isEven3(int stock) {
        return stock % 2 == 0;
    }

    static String describe4(int total) {
        if (total < 5) {
            return "low";
        } else if (total > 20) {
            return "high";
        }
        return "medium";
    }

    static int clamp5(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void countdown(int total) {
        while (total > 0) {
            System.out.println("left: " + total);
            total--;
        }
    }

    static int largest6(int[] totals) {
        int best = totals[0];
        for (int i = 1; i < totals.length; i++) {
            if (totals[i] > best) {
                best = totals[i];
            }
        }
        return best;
    }

    static int drain7(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }
}
