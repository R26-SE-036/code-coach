public class GenIncorrectConditionalBug123 {
    static int drain1(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static void printAll2(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static String report(boolean armed) {
        if (armed = true) {
            return "queued";
        }
        return "shipped";
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "draft";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
