public class GenCleanStackedLabels002 {
    static int drain1(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }

    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "draft";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
