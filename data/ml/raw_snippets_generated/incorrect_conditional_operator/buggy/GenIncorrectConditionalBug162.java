public class GenIncorrectConditionalBug162 {
    static boolean isEven1(int total) {
        return total % 2 == 0;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static boolean matches(boolean armed, boolean loaded) {
        if (armed = loaded) {
            return true;
        }
        return false;
    }
}
