public class GenWhileNoUpdateBug137 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void countdown(int budget) {
        while (budget > 0) {
            System.out.println("left: " + budget);
        }
    }

    static String describe4(int steps) {
        if (steps < 5) {
            return "low";
        } else if (steps > 20) {
            return "high";
        }
        return "medium";
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
