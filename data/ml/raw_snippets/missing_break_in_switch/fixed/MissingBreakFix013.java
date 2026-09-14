package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix013 {
    static String beats(String move) {
        String answer = "";
        switch (move) {
            case "rock":
                answer = "paper";
                break;
            case "paper":
                answer = "scissors";
                break;
            case "scissors":
                answer = "rock";
                break;
            default:
                answer = "invalid";
        }
        return answer;
    }
}
