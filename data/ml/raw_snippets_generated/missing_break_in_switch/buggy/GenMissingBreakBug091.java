public class GenMissingBreakBug091 {
    static String describe1(int steps) {
        if (steps < 5) {
            return "low";
        } else if (steps > 20) {
            return "high";
        }
        return "medium";
    }

    static int drain2(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "shipped";
            case 3:
                label = "closed";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static int drain3(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static boolean isEven4(int total) {
        return total % 2 == 0;
    }
}
