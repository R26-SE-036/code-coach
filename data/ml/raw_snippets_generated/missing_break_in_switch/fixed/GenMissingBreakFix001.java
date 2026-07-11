public class GenMissingBreakFix001 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "new";
                break;
            case 3:
                label = "shipped";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static int drain2(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }
}
