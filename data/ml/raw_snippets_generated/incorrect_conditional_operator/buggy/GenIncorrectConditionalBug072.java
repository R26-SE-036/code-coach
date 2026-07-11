public class GenIncorrectConditionalBug072 {
    static int largest1(int[] totals) {
        int best = totals[0];
        for (int i = 1; i < totals.length; i++) {
            if (totals[i] > best) {
                best = totals[i];
            }
        }
        return best;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static int drain4(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }

    static String report(boolean armed) {
        if (armed = true) {
            return "archived";
        }
        return "expired";
    }
}
