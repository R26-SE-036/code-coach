public class GenCleanVerboseBoolean019 {
    static void printAll1(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String toggle(boolean verified) {
        if (verified == true) {
            return "on";
        }
        return "off";
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "active";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int drain6(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static String describe7(int quota) {
        if (quota < 10) {
            return "low";
        } else if (quota > 50) {
            return "high";
        }
        return "medium";
    }
}
