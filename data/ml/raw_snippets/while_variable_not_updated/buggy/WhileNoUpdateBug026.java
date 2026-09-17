package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug026 {
    static int roundsSurvived(int health, int damage) {
        int rounds = 0;
        while (health > 0) {
            rounds++;
            int remaining = health - damage;
            System.out.println("Health would be " + remaining);
        }
        return rounds;
    }
}
