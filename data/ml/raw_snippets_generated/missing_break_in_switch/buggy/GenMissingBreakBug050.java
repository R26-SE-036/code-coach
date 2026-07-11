public class GenMissingBreakBug050 {
    static int drain1(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "active";
                break;
            case 3:
                label = "final";
            case 4:
                label = "expired";
                break;
            default:
                label = "draft";
        }
        return label;
    }
}
