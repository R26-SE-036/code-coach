public class GenMissingBreakFix023 {
    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "new";
                break;
            case 3:
                label = "archived";
                break;
            case 4:
                label = "draft";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static int drain1(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }
}
