public class GenWhileNoUpdateFix045 {
    static void pump(boolean enabled, int quota) {
        while (!enabled) {
            System.out.println(quota);
            quota++;
            enabled = quota > 10;
        }
    }
}
