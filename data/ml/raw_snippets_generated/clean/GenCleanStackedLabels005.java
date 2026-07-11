public class GenCleanStackedLabels005 {
    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "expired";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
