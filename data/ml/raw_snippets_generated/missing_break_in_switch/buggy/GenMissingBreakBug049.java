public class GenMissingBreakBug049 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static int drain2(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }

    static String describeItem(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "shipped";
            case 2:
                label = "expired";
                break;
            case 3:
                label = "active";
                break;
            default:
                label = "paid";
        }
        return label;
    }
}
