public class GenIncorrectConditionalBug107 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "active";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static boolean matches(boolean active, boolean armed) {
        if (active = armed) {
            return true;
        }
        return false;
    }

    static int drain2(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static boolean isEven4(int steps) {
        return steps % 2 == 0;
    }

    static String join5(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String status6(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static boolean isEven7(int level) {
        return level % 2 == 0;
    }

    static int sum8(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }
}
