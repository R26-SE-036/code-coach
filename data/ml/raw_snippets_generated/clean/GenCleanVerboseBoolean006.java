public class GenCleanVerboseBoolean006 {
    static String toggle(boolean done) {
        if (done == true) {
            return "on";
        }
        return "off";
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
