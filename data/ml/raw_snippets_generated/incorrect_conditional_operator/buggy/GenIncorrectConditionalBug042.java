public class GenIncorrectConditionalBug042 {
    static void announce(int limit) {
        if (limit = 5) {
            System.out.println("hit the target");
        }
    }

    static String describe1(int count) {
        if (count < 100) {
            return "low";
        } else if (count > 500) {
            return "high";
        }
        return "medium";
    }

    static boolean isEven2(int attempts) {
        return attempts % 2 == 0;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static boolean isEven4(int limit) {
        return limit % 2 == 0;
    }

    static int drain5(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }
}
