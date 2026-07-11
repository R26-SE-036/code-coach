public class GenCleanGeneric055 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int drain3(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }

    static void printAll4(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static String join5(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe6(int attempts) {
        if (attempts < 100) {
            return "low";
        } else if (attempts > 500) {
            return "high";
        }
        return "medium";
    }

    static String describe7(int quota) {
        if (quota < 100) {
            return "low";
        } else if (quota > 500) {
            return "high";
        }
        return "medium";
    }

    static String status8(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static int average9(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
