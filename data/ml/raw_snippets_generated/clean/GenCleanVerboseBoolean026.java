public class GenCleanVerboseBoolean026 {
    static String toggle(boolean open) {
        if (open == true) {
            return "on";
        }
        return "off";
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "draft";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static int drain2(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }

    static void printAll3(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }

    static int clamp4(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int clamp5(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
