public class GenMissingBreakFix013 {
    static int drain1(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }

    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "new";
                break;
            case 3:
                label = "draft";
                break;
            case 4:
                label = "expired";
                break;
            default:
                label = "archived";
        }
        return label;
    }
}
